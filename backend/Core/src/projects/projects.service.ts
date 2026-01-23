import { Injectable, NotFoundException, ForbiddenException, ConflictException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, Types } from 'mongoose';
import { Project, ProjectDocument } from './schemas/project.schema';
import { CreateProjectDto, UpdateProjectDto, CreateCheckpointDto, JoinProjectDto } from './dto';

@Injectable()
export class ProjectsService {
  constructor(
    @InjectModel(Project.name) private projectModel: Model<ProjectDocument>,
  ) {}

  async create(createProjectDto: CreateProjectDto, userId: string): Promise<ProjectDocument> {
    const project = new this.projectModel({
      ...createProjectDto,
      owner: new Types.ObjectId(userId),
      members: [
        {
          user: new Types.ObjectId(userId),
          role: 'owner',
          joinedAt: new Date(),
        },
      ],
    });
    return project.save();
  }

  async findAllForUser(userId: string): Promise<ProjectDocument[]> {
    return this.projectModel
      .find({
        'members.user': new Types.ObjectId(userId),
      })
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findById(id: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel
      .findById(id)
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .populate('checkpoints.createdBy', 'name email')
      .exec();

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check if user has access
    const hasAccess = project.members.some(
      (m) => m.user._id.toString() === userId,
    );

    if (!hasAccess) {
      throw new ForbiddenException('Access denied');
    }

    return project;
  }

  async update(
    id: string,
    updateProjectDto: UpdateProjectDto,
    userId: string,
  ): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(id).exec();

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check if user has edit access
    const member = project.members.find(
      (m) => m.user.toString() === userId,
    );

    if (!member || member.role === 'viewer') {
      throw new ForbiddenException('Access denied');
    }

    // Update allowed fields
    const allowedFields = [
      'name',
      'mainObjective',
      'secondaryObjectives',
      'description',
      'currentMode',
      'dataPool',
      'knowledgeGraph',
      'coScientistSteps',
    ];

    for (const field of allowedFields) {
      if (updateProjectDto[field] !== undefined) {
        project[field] = updateProjectDto[field];
      }
    }

    await project.save();

    const updatedProject = await this.projectModel
      .findById(id)
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .exec();

    if (!updatedProject) {
      throw new NotFoundException('Project not found');
    }

    return updatedProject;
  }

  async join(joinProjectDto: JoinProjectDto, userId: string): Promise<ProjectDocument> {
    const { hash } = joinProjectDto;

    const project = await this.projectModel
      .findOne({ hash: hash.toUpperCase() })
      .exec();

    if (!project) {
      throw new NotFoundException('Project not found. Check the join code.');
    }

    // Check if already a member
    const existingMember = project.members.find(
      (m) => m.user.toString() === userId,
    );

    if (existingMember) {
      throw new ConflictException('You are already a member of this project');
    }

    // Add user as editor
    project.members.push({
      user: new Types.ObjectId(userId),
      role: 'editor',
      joinedAt: new Date(),
    } as any);

    await project.save();

    const joinedProject = await this.projectModel
      .findById(project._id)
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .exec();

    if (!joinedProject) {
      throw new NotFoundException('Project not found');
    }

    return joinedProject;
  }

  async createCheckpoint(
    projectId: string,
    createCheckpointDto: CreateCheckpointDto,
    userId: string,
  ): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check access
    const member = project.members.find(
      (m) => m.user.toString() === userId,
    );

    if (!member || member.role === 'viewer') {
      throw new ForbiddenException('Access denied');
    }

    // Create checkpoint with current state
    const checkpoint = {
      _id: new Types.ObjectId(),
      name: createCheckpointDto.name,
      description: createCheckpointDto.description,
      mode: project.currentMode,
      dataPool: JSON.parse(JSON.stringify(project.dataPool)),
      knowledgeGraph: JSON.parse(JSON.stringify(project.knowledgeGraph)),
      coScientistSteps: JSON.parse(JSON.stringify(project.coScientistSteps)),
      createdBy: new Types.ObjectId(userId),
      createdAt: new Date(),
    };

    project.checkpoints.push(checkpoint as any);
    await project.save();

    return this.findById(projectId, userId);
  }

  async restoreCheckpoint(
    projectId: string,
    checkpointId: string,
    userId: string,
  ): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check access
    const member = project.members.find(
      (m) => m.user.toString() === userId,
    );

    if (!member || member.role === 'viewer') {
      throw new ForbiddenException('Access denied');
    }

    // Find checkpoint
    const checkpoint = project.checkpoints.find(
      (cp) => cp._id.toString() === checkpointId,
    );

    if (!checkpoint) {
      throw new NotFoundException('Checkpoint not found');
    }

    // Restore state from checkpoint
    project.currentMode = checkpoint.mode;
    project.dataPool = checkpoint.dataPool;
    project.knowledgeGraph = checkpoint.knowledgeGraph;
    project.coScientistSteps = checkpoint.coScientistSteps;

    await project.save();

    return this.findById(projectId, userId);
  }

  async delete(id: string, userId: string): Promise<void> {
    const project = await this.projectModel.findById(id).exec();

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Only owner can delete
    if (project.owner.toString() !== userId) {
      throw new ForbiddenException('Only the project owner can delete the project');
    }

    await this.projectModel.findByIdAndDelete(id).exec();
  }
}

import { Injectable, NotFoundException, ForbiddenException, ConflictException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, Types } from 'mongoose';
import { v4 as uuidv4 } from 'uuid';
import { Project, ProjectDocument } from './schemas/project.schema';
import { CreateProjectDto, UpdateProjectDto, CreateCheckpointDto, JoinProjectDto, AddCommentDto } from './dto';

type CheckpointPayload = {
  _id?: Types.ObjectId;
  name?: string;
  description?: string;
  mode?: string;
  dataPool?: any[];
  knowledgeGraph?: any;
  coScientistSteps?: any[];
  createdBy?: Types.ObjectId;
  createdAt?: Date;
};

@Injectable()
export class ProjectsService {
  constructor(
    @InjectModel(Project.name)
    private readonly projectModel: Model<ProjectDocument>,
  ) {}

  async create(createProjectDto: CreateProjectDto, userId: string): Promise<ProjectDocument> {
    const project = new this.projectModel({
      hash: uuidv4().substring(0, 8).toUpperCase(),
      name: createProjectDto.name,
      mainObjective: createProjectDto.mainObjective,
      secondaryObjectives: createProjectDto.secondaryObjectives ?? [],
      description: createProjectDto.description,
      owner: new Types.ObjectId(userId),
      members: [
        {
          user: new Types.ObjectId(userId),
          role: 'owner',
          joinedAt: new Date(),
        },
      ],
      currentMode: 'pool',
      dataPool: [],
      knowledgeGraph: { nodes: [], edges: [], groups: [] },
      coScientistSteps: [],
      checkpoints: [],
    });

    return project.save();
  }

  async findAllForUser(userId: string): Promise<ProjectDocument[]> {
    return this.projectModel
      .find({ 'members.user': new Types.ObjectId(userId) })
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .populate('dataPool.comments.author', 'name email')
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findById(id: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel
      .findById(id)
      .populate('owner', 'name email avatar')
      .populate('members.user', 'name email avatar')
      .populate('checkpoints.createdBy', 'name email')
      .populate('dataPool.comments.author', 'name email')
      .exec();

    if (!project) throw new NotFoundException('Project not found');

    const hasAccess = project.members.some(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!hasAccess) throw new ForbiddenException('Access denied');

    return project;
  }

  async update(id: string, dto: UpdateProjectDto, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(id).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    const allowed = [
      'name',
      'mainObjective',
      'secondaryObjectives',
      'constraints',
      'notes',
      'description',
      'currentMode',
      'dataPool',
      'knowledgeGraph',
      'coScientistSteps',
    ];

    for (const field of allowed) {
      if (dto[field] !== undefined) {
        project[field] = dto[field];
      }
    }

    await project.save();
    return this.findById(id, userId);
  }

  async join(dto: JoinProjectDto, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findOne({ hash: dto.hash.toUpperCase() }).exec();
    if (!project) throw new NotFoundException('Project not found');

    const exists = project.members.some(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (exists) throw new ConflictException('Already a member');

    project.members.push({
      user: new Types.ObjectId(userId),
      role: 'editor',
      joinedAt: new Date(),
    });

    await project.save();
    return this.findById(project._id.toString(), userId);
  }

  async createCheckpoint(projectId: string, dto: CreateCheckpointDto, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    project.checkpoints.push({
      _id: new Types.ObjectId(),
      name: dto.name,
      description: dto.description,
      mode: project.currentMode,
      dataPool: JSON.parse(JSON.stringify(project.dataPool)),
      knowledgeGraph: JSON.parse(JSON.stringify(project.knowledgeGraph)),
      coScientistSteps: JSON.parse(JSON.stringify(project.coScientistSteps)),
      createdBy: new Types.ObjectId(userId),
      createdAt: new Date(),
    });

    await project.save();
    return this.findById(projectId, userId);
  }

  async restoreCheckpoint(projectId: string, checkpointId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    const checkpoint = project.checkpoints.find(cp => cp._id.toString() === checkpointId);
    if (!checkpoint) throw new NotFoundException('Checkpoint not found');

    project.currentMode = checkpoint.mode;
    project.dataPool = checkpoint.dataPool;
    project.knowledgeGraph = checkpoint.knowledgeGraph;
    project.coScientistSteps = checkpoint.coScientistSteps;

    await project.save();
    return this.findById(projectId, userId);
  }

  async addComment(projectId: string, itemId: string, dto: AddCommentDto, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      // Handle both populated and unpopulated user references
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');

    const item = project.dataPool.find(i => i._id.toString() === itemId);
    if (!item) throw new NotFoundException('Item not found');

    item.comments.push({
      _id: new Types.ObjectId(),
      text: dto.text,
      author: new Types.ObjectId(userId),
      createdAt: new Date(),
    });

    await project.save();
    return this.findById(projectId, userId);
  }

  async deleteComment(projectId: string, itemId: string, commentId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const item = project.dataPool.find(i => i._id.toString() === itemId);
    if (!item) throw new NotFoundException('Item not found');

    const idx = item.comments.findIndex(c => c._id.toString() === commentId);
    if (idx === -1) throw new NotFoundException('Comment not found');

    // Handle both populated and unpopulated author references
    const authorId = item.comments[idx].author._id ? item.comments[idx].author._id.toString() : item.comments[idx].author.toString();
    if (authorId !== userId) throw new ForbiddenException();

    item.comments.splice(idx, 1);
    await project.save();

    return this.findById(projectId, userId);
  }

  async delete(id: string, userId: string): Promise<void> {
    const project = await this.projectModel.findById(id).exec();
    if (!project) throw new NotFoundException('Project not found');

    // Handle both populated and unpopulated owner references
    const ownerId = project.owner._id ? project.owner._id.toString() : project.owner.toString();
    if (ownerId !== userId) throw new ForbiddenException();
    await project.deleteOne();
  }
}
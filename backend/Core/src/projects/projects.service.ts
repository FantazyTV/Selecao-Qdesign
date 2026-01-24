import { Injectable, NotFoundException, ForbiddenException, ConflictException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { v4 as uuidv4 } from 'uuid';
import { Project } from './entities/project.entity';
import { CreateProjectDto, UpdateProjectDto, CreateCheckpointDto, JoinProjectDto } from './dto';

type CheckpointPayload = {
  id?: string;
  mode?: string;
  dataPool?: Array<Record<string, unknown>>;
  knowledgeGraph?: Record<string, unknown>;
  coScientistSteps?: Array<Record<string, unknown>>;
};

@Injectable()
export class ProjectsService {
  constructor(
    @InjectRepository(Project) private projectRepo: Repository<Project>,
  ) {}

  async create(createProjectDto: CreateProjectDto, userId: string): Promise<Project> {
    const project = this.projectRepo.create({
      hash: uuidv4().substring(0, 8).toUpperCase(),
      name: createProjectDto.name,
      mainObjective: createProjectDto.mainObjective,
      secondaryObjectives: createProjectDto.secondaryObjectives ?? [],
      description: createProjectDto.description,
      ownerId: userId,
      members: [
        {
          user: userId,
          role: 'owner',
          joinedAt: new Date().toISOString(),
        },
      ],
      currentMode: 'pool',
      dataPool: [],
      knowledgeGraph: { nodes: [], edges: [], groups: [] },
      coScientistSteps: [],
      checkpoints: [],
    });
    return this.projectRepo.save(project);
  }

  async findAllForUser(userId: string): Promise<Project[]> {
    return this.projectRepo
      .createQueryBuilder('project')
      .where('project.members @> :member', {
        member: JSON.stringify([{ user: userId }]),
      })
      .orderBy('project.updatedAt', 'DESC')
      .getMany();
  }

  async findById(id: string, userId: string): Promise<Project> {
    const project = await this.projectRepo.findOne({ where: { id } });

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check if user has access
    const hasAccess = (project.members || []).some(
      (m: any) => m.user === userId,
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
  ): Promise<Project> {
    const project = await this.projectRepo.findOne({ where: { id } });

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check if user has edit access
    const member = (project.members || []).find(
      (m: any) => m.user === userId,
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

    await this.projectRepo.save(project);

    const updatedProject = await this.projectRepo.findOne({ where: { id } });
    if (!updatedProject) {
      throw new NotFoundException('Project not found');
    }

    return updatedProject;
  }

  async join(joinProjectDto: JoinProjectDto, userId: string): Promise<Project> {
    const { hash } = joinProjectDto;

    const project = await this.projectRepo.findOne({ where: { hash: hash.toUpperCase() } });

    if (!project) {
      throw new NotFoundException('Project not found. Check the join code.');
    }

    // Check if already a member
    const existingMember = (project.members || []).find(
      (m: any) => m.user === userId,
    );

    if (existingMember) {
      throw new ConflictException('You are already a member of this project');
    }

    // Add user as editor
    project.members = project.members || [];
    project.members.push({
      user: userId,
      role: 'editor',
      joinedAt: new Date().toISOString(),
    });

    await this.projectRepo.save(project);

    const joinedProject = await this.projectRepo.findOne({ where: { id: project.id } });
    if (!joinedProject) {
      throw new NotFoundException('Project not found');
    }

    return joinedProject;
  }

  async createCheckpoint(
    projectId: string,
    createCheckpointDto: CreateCheckpointDto,
    userId: string,
  ): Promise<Project> {
    const project = await this.projectRepo.findOne({ where: { id: projectId } });

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check access
    const member = (project.members || []).find(
      (m: any) => m.user === userId,
    );

    if (!member || member.role === 'viewer') {
      throw new ForbiddenException('Access denied');
    }

    // Create checkpoint with current state
    const checkpoint = {
      id: uuidv4(),
      name: createCheckpointDto.name,
      description: createCheckpointDto.description,
      mode: project.currentMode,
      dataPool: JSON.parse(JSON.stringify(project.dataPool)),
      knowledgeGraph: JSON.parse(JSON.stringify(project.knowledgeGraph)),
      coScientistSteps: JSON.parse(JSON.stringify(project.coScientistSteps)),
      createdBy: userId,
      createdAt: new Date().toISOString(),
    };

    project.checkpoints = project.checkpoints || [];
    project.checkpoints.push(checkpoint as any);
    await this.projectRepo.save(project);

    return this.findById(projectId, userId);
  }

  async restoreCheckpoint(
    projectId: string,
    checkpointId: string,
    userId: string,
  ): Promise<Project> {
    const project = await this.projectRepo.findOne({ where: { id: projectId } });

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Check access
    const member = (project.members || []).find(
      (m: any) => m.user === userId,
    );

    if (!member || member.role === 'viewer') {
      throw new ForbiddenException('Access denied');
    }

    // Find checkpoint
    const checkpoint = (project.checkpoints || []).find(
      (cp: any) => cp.id === checkpointId,
    ) as CheckpointPayload | undefined;

    if (!checkpoint) {
      throw new NotFoundException('Checkpoint not found');
    }

    // Restore state from checkpoint
    project.currentMode = checkpoint.mode ?? project.currentMode;
    project.dataPool = checkpoint.dataPool ?? [];
    project.knowledgeGraph = checkpoint.knowledgeGraph ?? {};
    project.coScientistSteps = checkpoint.coScientistSteps ?? [];

    await this.projectRepo.save(project);

    return this.findById(projectId, userId);
  }

  async delete(id: string, userId: string): Promise<void> {
    const project = await this.projectRepo.findOne({ where: { id } });

    if (!project) {
      throw new NotFoundException('Project not found');
    }

    // Only owner can delete
    if (project.ownerId !== userId) {
      throw new ForbiddenException('Only the project owner can delete the project');
    }

    await this.projectRepo.delete({ id });
  }
}

import { Connection } from 'mongoose';
// Helper: get or create a GridFS bucket for large files
async function getGridFSBucket(mongooseConnection: any) {
  const { GridFSBucket } = await import('mongodb');
  return new GridFSBucket(mongooseConnection.db);
}

// --- Add GraphNode type with largeFileId ---
type GraphNode = {
  id: string;
  label?: string;
  fileUrl?: string;
  content?: string;
  largeFileId?: string;
  notes?: any[];
  [key: string]: any;
};

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
  // --- Helper: fetch large CIF from GridFS by fileId ---
  private async fetchLargeCifFromDb(fileId: string): Promise<string | null> {
    const mongoose = await import('mongoose');
    const conn = mongoose.connection;
    if (conn.readyState !== 1) {
      await new Promise((resolve, reject) => {
        conn.once('open', resolve);
        conn.once('error', reject);
      });
    }
    const bucket = await getGridFSBucket(conn);
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = [];
      bucket.openDownloadStream(new mongoose.Types.ObjectId(fileId))
        .on('data', (chunk) => chunks.push(chunk))
        .on('error', (err) => reject(err))
        .on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
    });
  }
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
    // --- Knowledge Graph Node Note CRUD ---
  async addNodeNote(projectId: string, nodeId: string, note: { text: string }, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    const node = project.knowledgeGraph.nodes.find(n => n.id === nodeId);
    if (!node) throw new NotFoundException('Node not found');

    // Add note with required fields
    node.notes.push({
      id: uuidv4(),
      text: note.text,
      author: new Types.ObjectId(userId),
      createdAt: new Date(),
    });

    // Ensure edges are not corrupted
    project.knowledgeGraph.edges = project.knowledgeGraph.edges.filter(e =>
      e && e.id && e.source && e.target && e.correlationType && typeof e.strength === 'number'
    );

    await project.save();
    return this.findById(projectId, userId);
  }
  // --- Knowledge Graph Node CRUD ---
  async updateNode(projectId: string, nodeId: string, update: Partial<any>, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    const node = project.knowledgeGraph.nodes.find(n => n.id === nodeId);
    if (!node) throw new NotFoundException('Node not found');

    // Prevent id from being updated or removed
    const { id, ...rest } = update;
    Object.assign(node, rest);
    await project.save();
    return this.findById(projectId, userId);
  }

  async deleteNode(projectId: string, nodeId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');

    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member || member.role === 'viewer') throw new ForbiddenException('Access denied');

    const nodeIndex = project.knowledgeGraph.nodes.findIndex(n => n.id === nodeId);
    if (nodeIndex === -1) throw new NotFoundException('Node not found');

    project.knowledgeGraph.nodes.splice(nodeIndex, 1);
    // Optionally, remove edges connected to this node
    project.knowledgeGraph.edges = project.knowledgeGraph.edges.filter(e => e.source !== nodeId && e.target !== nodeId);
    await project.save();
    return this.findById(projectId, userId);
  }
    // --- Project Retrieve Logic ---
  async retrieveProject(projectId: string, payload: any, userId: string): Promise<void> {
    // Validate user access to the project
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');
    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');

    // Only include allowed fields in the output payload
    const projectObj = project.toObject();
    const { hash, owner, members, currentMode, checkpoints, knowledgeGraph, coScientistSteps, __v, _id, ...rest } = projectObj;
    const outputPayload = { ...rest };

    // Send payload to microservice
    const axios = (await import('axios')).default;
    const dotenv = await import('dotenv');
    dotenv.config();
    const apiUrl = process.env.RETRIEVE_API_URL;
    if (!apiUrl) throw new Error('RETRIEVE_API_URL not set in .env');

    let response;
    try {
      response = await axios.post(apiUrl, outputPayload, { timeout: 10000 });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[RETRIEVE PAYLOAD] Error sending to microservice:', err);
      throw new Error('Failed to send payload to microservice');
    }

    // Poll for result (assume microservice returns a jobId or similar)
    let jobId = response.data.jobId || response.data.id || response.data.job_id;
    if (!jobId) throw new Error('Microservice did not return a jobId');

    // Polling loop (every 5s, up to 4min)
    let result = null;
    const pollUrl = apiUrl.replace(/\/?$/, '/') + 'result/' + jobId;
    const maxTries = 36; // 3min (5s interval)
    for (let i = 0; i < maxTries; i++) {
      try {
        const pollRes = await axios.get(pollUrl, { timeout: 10000 });
        if (pollRes.data && pollRes.data.status === 'done' && pollRes.data.graph) {
          result = pollRes.data.graph;
          break;
        }
        if (pollRes.data && pollRes.data.status === 'failed') {
          throw new Error('Microservice job failed');
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[RETRIEVE PAYLOAD] Polling error:', err);
      }
      await new Promise(res => setTimeout(res, 5000));
    }
    if (!result) throw new Error('Timed out waiting for microservice result');

    // Override knowledgeGraph in project
    project.knowledgeGraph = result;
    await project.save();
    // Optionally, emit event or notification here
    // eslint-disable-next-line no-console
    console.log('[RETRIEVE PAYLOAD] Knowledge graph updated for project', projectId);
  }

    // --- Fetch and cache CIF content for a node ---
  async fetchAndCacheCifContent(projectId: string, nodeId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');
    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');
    const node = project.knowledgeGraph.nodes.find((n: GraphNode) => n.id === nodeId);
    if (!node) throw new NotFoundException('Node not found');
    // If node.content is empty, try to load from DB or file
    if (!node.content && node.fileUrl) {
      // 1. Check if node.largeFileId exists (GridFS)
      if (node.largeFileId) {
        try {
          console.log('[CIF DEBUG] Attempting to load large CIF from DB, fileId:', node.largeFileId);
          const dbContent = await this.fetchLargeCifFromDb(node.largeFileId);
          if (dbContent) {
            node.content = dbContent;
            await project.save();
            console.log('[CIF DEBUG] Loaded large CIF from DB for node', nodeId);
            return this.findById(projectId, userId);
          }
        } catch (err) {
          console.error('[CIF DEBUG] Error loading large CIF from DB:', err);
        }
      }
      // 2. Try to load from file system
      const fs = await import('fs/promises');
      try {
        // Log the incoming fileUrl and cwd
        // eslint-disable-next-line no-console
        console.log('[CIF DEBUG] node.fileUrl:', node.fileUrl);
        console.log('[CIF DEBUG] process.cwd():', process.cwd());
        let filePath = node.fileUrl;
        if (!filePath.startsWith('/') && !filePath.match(/^[A-Za-z]:\\/)) {
          filePath = `${process.cwd()}/${filePath}`;
        }
        console.log('[CIF DEBUG] Resolved filePath:', filePath);
        const MAX_CIF_SIZE = 10 * 1024 * 1024; // 10MB
        const fileBuffer = await fs.readFile(filePath);
        if (fileBuffer.length > MAX_CIF_SIZE) {
          // Save to GridFS
          const mongoose = await import('mongoose');
          const conn = mongoose.connection;
          if (conn.readyState !== 1) {
            await new Promise((resolve, reject) => {
              conn.once('open', resolve);
              conn.once('error', reject);
            });
          }
          const bucket = await getGridFSBucket(conn);
          const uploadStream = bucket.openUploadStream(node.label || node.id || 'cif-file');
          uploadStream.end(fileBuffer);
          const fileId = uploadStream.id;
          node.largeFileId = fileId.toString();
          await new Promise((resolve, reject) => {
            uploadStream.on('finish', resolve);
            uploadStream.on('error', reject);
          });
          console.log('[CIF DEBUG] Saved large CIF to DB, fileId:', fileId);
        } else {
          node.content = fileBuffer.toString('utf-8');
        }
        await project.save();
        console.log('[CIF DEBUG] Successfully loaded CIF content for node', nodeId, 'size:', fileBuffer.length);
      } catch (err) {
        console.error('[CIF DEBUG] Error reading CIF file:', err);
        throw new NotFoundException('Could not read CIF file: ' + err);
      }
    }
    return this.findById(projectId, userId);
  }
    async aiAnalysis(projectId: string, payload: any, userId: string): Promise<void> {
    // AI Co-Scientist Analysis logic
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');
    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');

    // Only include allowed fields in the output payload
    const projectObj = project.toObject();
    const { hash, owner, members, currentMode, checkpoints, __v, _id, ...rest } = projectObj;
    const outputPayload = { ...rest };

    // Log to terminal
    // eslint-disable-next-line no-console
    console.log('[AI ANALYSIS PAYLOAD] Project data:', JSON.stringify(outputPayload, null, 2));

    // Write the filtered payload to a JSON file
    const fs = await import('fs/promises');
    const path = await import('path');
    const outputDir = path.join(process.cwd(), 'ai_analysis_payloads');
    try {
      await fs.mkdir(outputDir, { recursive: true });
      const fileName = `ai_analysis_${projectId}_${Date.now()}.json`;
      const filePath = path.join(outputDir, fileName);
      await fs.writeFile(filePath, JSON.stringify(outputPayload, null, 2), 'utf-8');
      // eslint-disable-next-line no-console
      console.log(`[AI ANALYSIS PAYLOAD] Written to: ${filePath}`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[AI ANALYSIS PAYLOAD] Error writing payload to file:', err);
      throw new Error('Failed to write payload to file');
    }
    // In the future: call external API endpoint (URL from .env)
    // Example:
    // const apiUrl = process.env.AI_ANALYSIS_API_URL;
    // await axios.post(apiUrl, outputPayload);
  }

}
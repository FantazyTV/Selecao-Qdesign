
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
      if (!m.user) return false; // Skip null users (deleted users)
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

    // Send payload to async /process endpoint
    const axios = (await import('axios')).default;
    const dotenv = await import('dotenv');
    dotenv.config();
    const baseUrl = process.env.RETRIEVE_API_URL;
    if (!baseUrl) throw new Error('RETRIEVE_API_URL not set in .env');
    const processUrl = baseUrl.replace(/\/?$/, '/') + 'retrieval/process';

    console.log(outputPayload);
    let response;
    try {
      response = await axios.post(processUrl, outputPayload, { timeout: 20000 });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[RETRIEVE PAYLOAD] Error sending to async /retireval/process:', err);
      throw new Error('Failed to send payload to async retrieval service');
    }

    // Get jobId from response
    const jobId = response.data.jobId || response.data.id || response.data.job_id;
    if (!jobId) throw new Error('Async retrieval service did not return a jobId');

    // Poll for job completion using /status/{jobId}
    const statusUrl = baseUrl.replace(/\/?$/, '/') + 'retrieval/status/' + jobId;
    const resultUrl = baseUrl.replace(/\/?$/, '/') + 'retrieval/result/' + jobId;
    const maxPolls = 24; // 2 minutes at 5s intervals
    let pollCount = 0;
    let status = null;
    let failed = false;
    while (pollCount < maxPolls) {
      pollCount++;
      try {
        const statusRes = await axios.get(statusUrl, { timeout: 10000 });
        if (statusRes.status === 200 && statusRes.data) {
          status = statusRes.data.status;
          if (status === 'completed') {
            break;
          } else if (status === 'failed') {
            failed = true;
            // eslint-disable-next-line no-console
            console.error('[RETRIEVE PAYLOAD] Job failed:', statusRes.data.error);
            throw new Error('Async retrieval job failed: ' + (statusRes.data.error || 'Unknown error'));
          }
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[RETRIEVE PAYLOAD] Polling error:', err);
      }
      await new Promise(res => setTimeout(res, 5000));
    }
    if (failed) throw new Error('Async retrieval job failed');
    if (status !== 'completed') throw new Error('Timed out waiting for async retrieval job completion');

    // Fetch result from /result/{jobId}
    let resultData;
    try {
      const resultRes = await axios.get(resultUrl, { timeout: 20000 });
      if (resultRes.status === 200 && resultRes.data && resultRes.data.graph) {
        resultData = resultRes.data;
      } else {
        throw new Error('Result missing graph data');
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[RETRIEVE PAYLOAD] Error fetching result:', err);
      throw new Error('Failed to fetch result from async retrieval service');
    }

    // Persist the returned graph to the project
    project.knowledgeGraph = resultData.graph;
    await project.save();

    // Emit socket event to notify frontend
    try {
      const { emitProjectUpdate } = await import('../socket-emitter.js');
      emitProjectUpdate(projectId, project.toObject());
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[RETRIEVE PAYLOAD] Error emitting project:update event:', err);
    }

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
    // --- Fetch and cache PDF content for a node ---
  async fetchAndCachePdfContent(projectId: string, nodeId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');
    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');
    const node = project.knowledgeGraph.nodes.find((n: GraphNode) => n.id === nodeId);
    if (!node) throw new NotFoundException('Node not found');
    // If node.content is empty, try to load from file
    if (!node.content && node.fileUrl) {
      try {
        const fs = await import('fs/promises');
        const path = await import('path');
        const filePath = path.resolve(node.fileUrl);
        const dataBuffer = await fs.readFile(filePath);
        // Return base64 encoded PDF data
        node.content = `data:application/pdf;base64,${dataBuffer.toString('base64')}`;
      } catch (err) {
        node.content = 'Failed to load PDF content.';
      }
      await project.save();
    }
    return this.findById(projectId, userId);
  }

  // --- Fetch and cache Image content for a node ---
  async fetchAndCacheImageContent(projectId: string, nodeId: string, userId: string): Promise<ProjectDocument> {
    const project = await this.projectModel.findById(projectId).exec();
    if (!project) throw new NotFoundException('Project not found');
    const member = project.members.find(m => {
      const memberUserId = m.user._id ? m.user._id.toString() : m.user.toString();
      return memberUserId === userId;
    });
    if (!member) throw new ForbiddenException('Access denied');
    const node = project.knowledgeGraph.nodes.find((n: GraphNode) => n.id === nodeId);
    if (!node) throw new NotFoundException('Node not found');
    // If node.content is empty, try to load from file
    if (!node.content && node.fileUrl) {
      try {
        const fs = await import('fs/promises');
        const path = await import('path');
        const filePath = path.resolve(node.fileUrl);
        const imageBuffer = await fs.readFile(filePath);
        const ext = path.extname(filePath).replace('.', '').toLowerCase();
        const mimeType = ext === 'jpg' ? 'jpeg' : ext;
        node.content = `data:image/${mimeType};base64,${imageBuffer.toString('base64')}`;
      } catch (err) {
        node.content = 'Failed to load image content.';
      }
      await project.save();
    }
    return this.findById(projectId, userId);
  }

    async expandNode(projectId: string, payload: any): Promise<void> {
        // Log the received request (including prompt)
        console.log('[EXPAND SERVICE]', { projectId, payload });
        // Use the expand service, expect the whole updated knowledge graph in return
        const axios = (await import('axios')).default;
        // The expand service URL (adjust if needed)
        // New route: /api/v1/expand/process
        const EXPAND_API_URL = process.env.EXPAND_API_URL || 'http://localhost:8000/api/v1/expand/process';
        // Send expand request with node
        const node = payload.node;
        if (!node) throw new Error('Node is required for expand');
        // 1. Send expand request
        const { data: startResp } = await axios.post(EXPAND_API_URL, { node });
        const jobId = startResp.jobId;
        if (!jobId) throw new Error('Expand jobId missing');
        // 2. Poll for result
        const STATUS_URL = (process.env.EXPAND_API_URL || 'http://localhost:8000/api/v1/expand').replace(/\/process$/, '') + `/status/${jobId}`;
        const RESULT_URL = (process.env.EXPAND_API_URL || 'http://localhost:8000/api/v1/expand').replace(/\/process$/, '') + `/result/${jobId}`;
        let status = 'processing';
        let tries = 0;
        let result: any = null;
        while (status === 'processing' && tries < 20) {
          await new Promise(res => setTimeout(res, 1000));
          const { data: statusResp } = await axios.get(STATUS_URL);
          status = statusResp.status;
          if (status === 'completed') {
            const { data: resData } = await axios.get(RESULT_URL);
            result = resData as any;
            break;
          } else if (status === 'failed') {
            throw new Error('Expand job failed: ' + statusResp.error);
          }
          tries++;
        }
        if (!result) throw new Error('Expand did not complete');
        // 3. Replace the knowledge graph with the returned one
        const project = await this.projectModel.findById(projectId).exec();
        if (!project) throw new Error('Project not found');
        if (!result || typeof result !== 'object' || !('knowledgeGraph' in result)) throw new Error('Expand result missing knowledgeGraph');
        project.knowledgeGraph = (result as any).knowledgeGraph;
        await project.save();
    }
  }
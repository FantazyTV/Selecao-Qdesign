import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types } from 'mongoose';
import { v4 as uuidv4 } from 'uuid';


@Schema({ _id: false })
export class DataPoolItem {
  @Prop({ default: () => new Types.ObjectId() })
  _id: Types.ObjectId;

  @Prop({ required: true, enum: ['pdb', 'pdf', 'image', 'sequence', 'text', 'other'] })
  type: string;

  @Prop({ required: true })
  name: string;

  @Prop()
  description?: string;

  @Prop()
  content?: string;

  @Prop()
  fileUrl?: string;

  @Prop({ type: Object })
  metadata?: Record<string, unknown>;

  @Prop({ type: Types.ObjectId, ref: 'User', required: true })
  addedBy: Types.ObjectId;

  @Prop({ default: Date.now })
  addedAt: Date;
}

export const DataPoolItemSchema = SchemaFactory.createForClass(DataPoolItem);

@Schema({ _id: false })
export class GraphNodeNote {
  @Prop({ default: () => uuidv4() })
  id: string;

  @Prop({ required: true })
  text: string;

  @Prop({ type: Types.ObjectId, ref: 'User' })
  author: Types.ObjectId;

  @Prop({ default: Date.now })
  createdAt: Date;
}

export const GraphNodeNoteSchema = SchemaFactory.createForClass(GraphNodeNote);

@Schema({ _id: false })
export class GraphNode {
  @Prop({ required: true })
  id: string;

  @Prop({ required: true, enum: ['pdb', 'pdf', 'image', 'sequence', 'text', 'retrieved', 'annotation'] })
  type: string;

  @Prop({ required: true })
  label: string;

  @Prop()
  description?: string;

  @Prop()
  content?: string;

  @Prop()
  fileUrl?: string;

  @Prop({ type: { x: Number, y: Number }, required: true })
  position: { x: number; y: number };

  @Prop({ required: true, enum: ['high', 'medium', 'low', 'untrusted'], default: 'medium' })
  trustLevel: string;

  @Prop({ type: [GraphNodeNoteSchema], default: [] })
  notes: GraphNodeNote[];

  @Prop({ type: Object })
  metadata?: Record<string, unknown>;

  @Prop()
  groupId?: string;
}

export const GraphNodeSchema = SchemaFactory.createForClass(GraphNode);

@Schema({ _id: false })
export class GraphEdge {
  @Prop({ required: true })
  id: string;

  @Prop({ required: true })
  source: string;

  @Prop({ required: true })
  target: string;

  @Prop()
  label?: string;

  @Prop({ required: true, enum: ['similar', 'cites', 'contradicts', 'supports', 'derived', 'custom'] })
  correlationType: string;

  @Prop({ required: true, min: 0, max: 1 })
  strength: number;

  @Prop()
  explanation?: string;

  @Prop({ type: Object })
  metadata?: Record<string, unknown>;
}

export const GraphEdgeSchema = SchemaFactory.createForClass(GraphEdge);

@Schema({ _id: false })
export class GraphGroup {
  @Prop({ required: true })
  id: string;

  @Prop({ required: true })
  name: string;

  @Prop({ required: true })
  color: string;
}

export const GraphGroupSchema = SchemaFactory.createForClass(GraphGroup);

@Schema({ _id: false })
export class KnowledgeGraph {
  @Prop({ type: [GraphNodeSchema], default: [] })
  nodes: GraphNode[];

  @Prop({ type: [GraphEdgeSchema], default: [] })
  edges: GraphEdge[];

  @Prop({ type: [GraphGroupSchema], default: [] })
  groups: GraphGroup[];
}

export const KnowledgeGraphSchema = SchemaFactory.createForClass(KnowledgeGraph);

@Schema({ _id: false })
export class StepAttachment {
  @Prop({ required: true, enum: ['pdb', 'pdf', 'image', 'text'] })
  type: string;

  @Prop({ required: true })
  name: string;

  @Prop()
  content?: string;

  @Prop()
  fileUrl?: string;
}

export const StepAttachmentSchema = SchemaFactory.createForClass(StepAttachment);

@Schema({ _id: false })
export class StepComment {
  @Prop({ default: () => uuidv4() })
  id: string;

  @Prop({ required: true })
  text: string;

  @Prop({ type: Types.ObjectId, ref: 'User' })
  author: Types.ObjectId;

  @Prop({ default: Date.now })
  createdAt: Date;
}

export const StepCommentSchema = SchemaFactory.createForClass(StepComment);

@Schema({ _id: false })
export class CoScientistStep {
  @Prop({ default: () => uuidv4() })
  id: string;

  @Prop({ required: true, enum: ['reasoning', 'evidence', 'hypothesis', 'conclusion', 'question', 'design'] })
  type: string;

  @Prop({ required: true })
  title: string;

  @Prop({ required: true })
  content: string;

  @Prop({ type: [StepAttachmentSchema], default: [] })
  attachments: StepAttachment[];

  @Prop({ type: [StepCommentSchema], default: [] })
  comments: StepComment[];

  @Prop({ required: true, enum: ['pending', 'approved', 'rejected', 'modified'], default: 'pending' })
  status: string;

  @Prop({ default: Date.now })
  createdAt: Date;
}

export const CoScientistStepSchema = SchemaFactory.createForClass(CoScientistStep);

@Schema({ _id: false })
export class ProjectMember {
  @Prop({ type: Types.ObjectId, ref: 'User', required: true })
  user: Types.ObjectId;

  @Prop({ required: true, enum: ['owner', 'editor', 'viewer'] })
  role: string;

  @Prop({ default: Date.now })
  joinedAt: Date;
}

export const ProjectMemberSchema = SchemaFactory.createForClass(ProjectMember);

@Schema({ _id: false })
export class Checkpoint {
  @Prop({ default: () => new Types.ObjectId() })
  _id: Types.ObjectId;

  @Prop({ required: true })
  name: string;

  @Prop()
  description?: string;

  @Prop({ required: true, enum: ['pool', 'retrieval', 'coscientist'] })
  mode: string;

  @Prop({ type: [DataPoolItemSchema], default: [] })
  dataPool: DataPoolItem[];

  @Prop({ type: KnowledgeGraphSchema, default: () => ({ nodes: [], edges: [], groups: [] }) })
  knowledgeGraph: KnowledgeGraph;

  @Prop({ type: [CoScientistStepSchema], default: [] })
  coScientistSteps: CoScientistStep[];

  @Prop({ type: Types.ObjectId, ref: 'User', required: true })
  createdBy: Types.ObjectId;

  @Prop({ default: Date.now })
  createdAt: Date;
}

export const CheckpointSchema = SchemaFactory.createForClass(Checkpoint);

// Main Project Schema
export type ProjectDocument = Project & Document;

@Schema({ timestamps: true })
export class Project {
  @Prop({ required: true, unique: true, default: () => uuidv4().substring(0, 8).toUpperCase() })
  hash: string;

  @Prop({ required: true })
  name: string;

  @Prop({ required: true })
  mainObjective: string;

  @Prop({ type: [String], default: [] })
  secondaryObjectives: string[];

  @Prop()
  description?: string;

  @Prop({ type: Types.ObjectId, ref: 'User', required: true })
  owner: Types.ObjectId;

  @Prop({ type: [ProjectMemberSchema], default: [] })
  members: ProjectMember[];

  @Prop({ required: true, enum: ['pool', 'retrieval', 'coscientist'], default: 'pool' })
  currentMode: string;

  @Prop({ type: [DataPoolItemSchema], default: [] })
  dataPool: DataPoolItem[];

  @Prop({ type: KnowledgeGraphSchema, default: () => ({ nodes: [], edges: [], groups: [] }) })
  knowledgeGraph: KnowledgeGraph;

  @Prop({ type: [CoScientistStepSchema], default: [] })
  coScientistSteps: CoScientistStep[];

  @Prop({ type: [CheckpointSchema], default: [] })
  checkpoints: Checkpoint[];
}

export const ProjectSchema = SchemaFactory.createForClass(Project);

// Virtual for id
ProjectSchema.virtual('id').get(function () {
  return this._id.toHexString();
});

// Ensure virtuals are included in JSON
ProjectSchema.set('toJSON', {
  virtuals: true,
  transform: (_, ret) => {
    const obj = ret as unknown as Record<string, unknown>;
    delete obj.__v;
    return obj;
  },
});

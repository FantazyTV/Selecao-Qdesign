import { IsString, IsOptional, IsArray, IsEnum, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';

class DataPoolItemDto {
  @IsString()
  @IsOptional()
  _id?: string;

  @IsString()
  type: string;

  @IsString()
  name: string;

  @IsString()
  @IsOptional()
  description?: string;

  @IsString()
  @IsOptional()
  content?: string;

  @IsString()
  @IsOptional()
  fileUrl?: string;

  @IsOptional()
  metadata?: Record<string, unknown>;

  @IsString()
  @IsOptional()
  addedBy?: string;

  @IsString()
  @IsOptional()
  addedAt?: string;
}

class GraphNodeDto {
  @IsString()
  id: string;

  @IsString()
  type: string;

  @IsString()
  label: string;

  @IsOptional()
  description?: string;

  @IsOptional()
  content?: string;

  @IsOptional()
  fileUrl?: string;

  @IsOptional()
  position?: { x: number; y: number };

  @IsOptional()
  trustLevel?: string;

  @IsOptional()
  notes?: any[];

  @IsOptional()
  metadata?: Record<string, unknown>;

  @IsOptional()
  groupId?: string;
}

class GraphEdgeDto {
  @IsString()
  id: string;

  @IsString()
  source: string;

  @IsString()
  target: string;

  @IsOptional()
  label?: string;

  @IsString()
  correlationType: string;

  @IsOptional()
  strength?: number;

  @IsOptional()
  explanation?: string;
}

class GraphGroupDto {
  @IsString()
  id: string;

  @IsString()
  name: string;

  @IsString()
  color: string;
}

class KnowledgeGraphDto {
  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => GraphNodeDto)
  nodes?: GraphNodeDto[];

  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => GraphEdgeDto)
  edges?: GraphEdgeDto[];

  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => GraphGroupDto)
  groups?: GraphGroupDto[];
}

class CoScientistStepDto {
  @IsString()
  @IsOptional()
  id?: string;

  @IsString()
  type: string;

  @IsString()
  title: string;

  @IsString()
  content: string;

  @IsOptional()
  attachments?: any[];

  @IsOptional()
  comments?: any[];

  @IsString()
  @IsOptional()
  status?: string;

  @IsOptional()
  createdAt?: string;
}

export class UpdateProjectDto {
  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsOptional()
  mainObjective?: string;

  @IsArray()
  @IsOptional()
  @IsString({ each: true })
  secondaryObjectives?: string[];

  @IsArray()
  @IsOptional()
  @IsString({ each: true })
  constraints?: string[];

  @IsArray()
  @IsOptional()
  @IsString({ each: true })
  notes?: string[];

  @IsString()
  @IsOptional()
  description?: string;

  @IsEnum(['pool', 'retrieval', 'coscientist'])
  @IsOptional()
  currentMode?: string;

  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => DataPoolItemDto)
  dataPool?: DataPoolItemDto[];

  @IsOptional()
  @ValidateNested()
  @Type(() => KnowledgeGraphDto)
  knowledgeGraph?: KnowledgeGraphDto;

  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => CoScientistStepDto)
  coScientistSteps?: CoScientistStepDto[];
}

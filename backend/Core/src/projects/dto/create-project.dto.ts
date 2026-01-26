import { IsString, IsNotEmpty, IsOptional, IsArray } from 'class-validator';

export class CreateProjectDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @IsString()
  @IsNotEmpty()
  mainObjective: string;

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
}

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

  @IsString()
  @IsOptional()
  description?: string;
}

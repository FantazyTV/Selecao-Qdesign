import { IsString, IsNotEmpty, IsOptional } from 'class-validator';

export class CreateCheckpointDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @IsString()
  @IsOptional()
  description?: string;
}

import {
  Controller,
  Get,
  Post,
  Patch,
  Delete,
  Body,
  Param,
  UseGuards,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { ProjectsService } from './projects.service';
import { CreateProjectDto, UpdateProjectDto, CreateCheckpointDto, JoinProjectDto, AddCommentDto } from './dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import type { CurrentUserData } from '../auth/decorators/current-user.decorator';

@Controller('projects')
@UseGuards(JwtAuthGuard)
export class ProjectsController {
  constructor(private readonly projectsService: ProjectsService) {}

  @Post()
  async create(
    @Body() createProjectDto: CreateProjectDto,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.create(createProjectDto, user.userId);
    return { project };
  }

  @Get()
  async findAll(@CurrentUser() user: CurrentUserData) {
    const projects = await this.projectsService.findAllForUser(user.userId);
    return { projects };
  }

  @Get(':id')
  async findOne(
    @Param('id') id: string,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.findById(id, user.userId);
    // console.log(project);
    return { project };
  }

  @Patch(':id')
  async update(
    @Param('id') id: string,
    @Body() updateProjectDto: UpdateProjectDto,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.update(id, updateProjectDto, user.userId);
    return { project };
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async remove(
    @Param('id') id: string,
    @CurrentUser() user: CurrentUserData,
  ) {
    await this.projectsService.delete(id, user.userId);
  }

  @Post('join')
  async join(
    @Body() joinProjectDto: JoinProjectDto,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.join(joinProjectDto, user.userId);
    return { project, message: 'Joined project successfully' };
  }

  @Post(':id/checkpoints')
  async createCheckpoint(
    @Param('id') id: string,
    @Body() createCheckpointDto: CreateCheckpointDto,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.createCheckpoint(
      id,
      createCheckpointDto,
      user.userId,
    );
    const checkpoint = project.checkpoints[project.checkpoints.length - 1];
    return { checkpoint, project };
  }

  @Post(':id/checkpoints/:checkpointId/restore')
  async restoreCheckpoint(
    @Param('id') id: string,
    @Param('checkpointId') checkpointId: string,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.restoreCheckpoint(
      id,
      checkpointId,
      user.userId,
    );
    return { project, message: 'Checkpoint restored' };
  }

  @Post(':id/data-pool/:itemId/comments')
  async addComment(
    @Param('id') id: string,
    @Param('itemId') itemId: string,
    @Body() addCommentDto: AddCommentDto,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.addComment(
      id,
      itemId,
      addCommentDto,
      user.userId,
    );
    return { project };
  }

  @Delete(':id/data-pool/:itemId/comments/:commentId')
  async deleteComment(
    @Param('id') id: string,
    @Param('itemId') itemId: string,
    @Param('commentId') commentId: string,
    @CurrentUser() user: CurrentUserData,
  ) {
    const project = await this.projectsService.deleteComment(
      id,
      itemId,
      commentId,
      user.userId,
    );
    return { project };
  }
}

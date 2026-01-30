import {
  Controller,
  Post,
  Body,
  Param,
} from '@nestjs/common';
import { ProjectsService } from './projects.service';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import type { CurrentUserData } from '../auth/decorators/current-user.decorator';

@Controller('projects')
export class ExpandController {
  constructor(private readonly projectsService: ProjectsService) {}

  @Post(':id/expand')
  async expandNode(
    @Param('id') id: string,
    @Body() payload: any,
  ) {
    // Log the received request
    console.log('[EXPAND REQUEST]', { projectId: id, payload });
    await this.projectsService.expandNode(id, payload);
    return { message: 'Expand request received' };
  }
}

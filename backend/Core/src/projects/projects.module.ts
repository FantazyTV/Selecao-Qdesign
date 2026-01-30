import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ProjectsController } from './projects.controller';
import { ExpandController } from './expand.controller';
import { ProjectsService } from './projects.service';
import { Project, ProjectSchema } from './schemas/project.schema';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: Project.name, schema: ProjectSchema }]),
    AuthModule,
  ],
  controllers: [ProjectsController, ExpandController],
  providers: [ProjectsService],
  exports: [ProjectsService],
})
export class ProjectsModule {}

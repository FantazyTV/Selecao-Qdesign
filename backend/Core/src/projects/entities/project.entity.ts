import {
  Column,
  CreateDateColumn,
  Entity,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('projects')
export class Project {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  hash: string;

  @Column()
  name: string;

  @Column()
  mainObjective: string;

  @Column('text', { array: true, default: () => 'ARRAY[]::text[]' })
  secondaryObjectives: string[];

  @Column({ nullable: true })
  description?: string;

  @Column()
  ownerId: string;

  @Column('jsonb', { default: () => `'[]'::jsonb` })
  members: Array<Record<string, unknown>>;

  @Column({ default: 'pool' })
  currentMode: string;

  @Column('jsonb', { default: () => `'[]'::jsonb` })
  dataPool: Array<Record<string, unknown>>;

  @Column('jsonb', { default: () => `'{}'::jsonb` })
  knowledgeGraph: Record<string, unknown>;

  @Column('jsonb', { default: () => `'[]'::jsonb` })
  coScientistSteps: Array<Record<string, unknown>>;

  @Column('jsonb', { default: () => `'[]'::jsonb` })
  checkpoints: Array<Record<string, unknown>>;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}

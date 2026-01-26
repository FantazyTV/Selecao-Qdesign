import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type UserDocument = User & Document;

@Schema({ timestamps: true })
export class User {
  @Prop({ required: true })
  name: string;

  @Prop({ required: true, unique: true })
  email: string;

  @Prop({ required: true })
  password: string;

  @Prop()
  avatar?: string;

  // Virtual property for id
  id: string;
}

export const UserSchema = SchemaFactory.createForClass(User);

// Virtual for id
UserSchema.virtual('id').get(function () {
  return this._id.toHexString();
});

// Ensure virtuals are included in JSON
UserSchema.set('toJSON', {
  virtuals: true,
  transform: (_, ret) => {
    const obj = ret as unknown as Record<string, unknown>;
    delete obj.__v;
    delete obj._id;
    return obj;
  },
});

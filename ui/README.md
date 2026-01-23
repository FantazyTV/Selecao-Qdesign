# QDesign - AI-Driven Biological Design Platform

QDesign is a collaborative, AI-driven biological design platform that allows scientists to explore existing biological knowledge, generate new protein designs, and iteratively refine them using evidence-based reasoning.

## Features

- **Data Pool (Mode 0)**: Upload and manage research data including PDB structures, PDFs, images, sequences, and text files
- **Knowledge Graph (Mode 1)**: Visualize and connect research artifacts with trust levels and correlation types
- **AI Co-Scientist (Mode 2)**: AI-powered reasoning sidebar that generates insights, hypotheses, and design suggestions
- **Real-time Collaboration**: Multi-user collaboration with WebSocket support
- **Checkpoints**: Save and restore project states at any point
- **File Viewers**: Built-in viewers for PDB 3D structures, PDFs, images, and sequences
- **IEEE PDF Export**: Export research findings to IEEE-format PDF

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **State Management**: Zustand, TanStack Query
- **Database**: MongoDB with Mongoose
- **Auth**: JWT with HTTP-only cookies
- **Real-time**: Socket.io
- **Visualization**: @xyflow/react (knowledge graph), NGL (3D structures)
- **PDF**: react-pdf (viewing), jsPDF (export)

## Getting Started

### Prerequisites

- Node.js 18+
- MongoDB (local or Atlas)
- pnpm (recommended)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pnpm install
```

3. Copy the environment file and configure:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your settings:

```env
MONGODB_URI=mongodb://localhost:27017/qdesign
JWT_SECRET=your-super-secret-jwt-key
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_SOCKET_URL=http://localhost:3001
SOCKET_PORT=3001
```

4. Start MongoDB:

```bash
# If using local MongoDB
mongod
```

### Development

Run both the Next.js app and WebSocket server:

```bash
pnpm dev:all
```

Or run them separately:

```bash
# Terminal 1 - Next.js
pnpm dev

# Terminal 2 - WebSocket server
pnpm dev:socket
```

Open [http://localhost:3000](http://localhost:3000) to access the application.

## Project Structure

```
ui/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth pages (login, register)
│   ├── (landing)/         # Landing page
│   ├── api/               # API routes
│   ├── dashboard/         # Dashboard page
│   └── project/[id]/      # Project workspace
├── components/
│   ├── dialogs/           # Modal dialogs
│   ├── ui/                # Base UI components
│   ├── viewers/           # File viewers (PDB, PDF, etc.)
│   └── workspace/         # Workspace components
├── hooks/                 # Custom React hooks
├── lib/
│   ├── models/           # MongoDB models
│   ├── auth.ts           # Authentication utilities
│   ├── db.ts             # Database connection
│   ├── socket.tsx        # Socket.io client
│   ├── stores.ts         # Zustand stores
│   ├── types.ts          # TypeScript types
│   └── utils.ts          # Utility functions
└── server/
    └── socket.ts         # WebSocket server
```

## Usage

### Creating a Project

1. Sign up or log in
2. Click "New Project" from the dashboard
3. Enter project details and create

### Inviting Collaborators

1. Open a project
2. Click the "Share" button
3. Copy the unique project code
4. Share with collaborators

### Data Pool Mode

- Drag and drop files to upload
- Supported formats: PDB, CIF, PDF, PNG, JPG, FASTA, TXT
- Click items to view in floating windows

### Knowledge Graph Mode

- Add nodes from the data pool
- Connect nodes with edges (supports, contradicts, similar, etc.)
- Set trust levels for nodes
- Add notes and annotations

### AI Co-Scientist Mode

- Click "Start Analysis" to begin AI-driven analysis
- Review generated steps (reasoning, evidence, hypotheses, conclusions)
- Approve or reject suggestions
- Add comments and feedback
- Export to IEEE-format PDF

## License

MIT

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

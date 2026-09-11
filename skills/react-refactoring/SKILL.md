---
name: react-refactoring
description: React refactoring practices for promoting SRP, DRY, KISS, extracting custom hooks, splitting large components, and managing UI state with Zustand. Use when refactoring React components, reducing complexity, or improving code organization.
---

# React Refactoring

## Guiding Principles

1. **SRP** - One component = one reason to change. If you describe a component with "and", split it.
2. **DRY** - Extract repeated JSX into components, repeated logic into hooks.
3. **KISS** - Prefer the simplest solution. Don't abstract until you must.
4. **YAGNI** - Don't build for hypothetical futures. Refactor when the need is real.

## Identifying Refactoring Targets

### Component Smells

- **> 150 lines** - Almost always needs splitting.
- **> 3 `useState` calls** - Extract into a custom hook or Zustand slice.
- **Nested ternaries in JSX** - Extract into sub-components or a render map.
- **Multiple `useEffect` with unrelated deps** - Each effect should have a single concern; consider separate hooks.
- **Prop drilling > 2 levels** - Use Zustand, context, or composition.
- **Mixed concerns** - Data fetching + rendering + form handling in one component.

### Hook Smells

- **Hook doing multiple unrelated things** - Split into focused hooks.
- **Hook > 50 lines** - Likely doing too much.
- **Hook with > 5 return values** - Return an object, or split the hook.

## Splitting Large Components

### Strategy: Top-Down Decomposition

Identify the visual/logical sections, then extract from the leaves up.

```
// BEFORE: One monolithic component
ProjectDashboard (400 lines)
  ├── header with stats
  ├── filter bar
  ├── project list with cards
  └── pagination

// AFTER: Composed from focused pieces
ProjectDashboard (50 lines - orchestrator)
  ├── ProjectStats
  ├── ProjectFilterBar
  ├── ProjectList
  │   └── ProjectCard
  └── Pagination
```

### Pattern: Container / Presentational Split

Separate data logic from rendering:

```tsx
// Container: owns the data + logic
function ProjectListContainer() {
  const { projects, isLoading } = useProjects();
  const { filters, setFilter } = useProjectFilters();

  if (isLoading) return <ProjectListSkeleton />;

  return (
    <ProjectList
      projects={projects}
      filters={filters}
      onFilterChange={setFilter}
    />
  );
}

// Presentational: pure rendering, easy to test
function ProjectList({ projects, filters, onFilterChange }: IProjectListProps) {
  return (
    <div className="space-y-4">
      <ProjectFilterBar filters={filters} onChange={onFilterChange} />
      {projects.map(p => (
        <ProjectCard key={p.id} project={p} />
      ))}
    </div>
  );
}
```

### Pattern: Composition via Children

Avoid prop drilling by composing with `children`:

```tsx
// ❌ Drilling callbacks through layers
<Dashboard onEdit={handleEdit} onDelete={handleDelete} onShare={handleShare}>
  <ProjectList onEdit={handleEdit} onDelete={handleDelete} onShare={handleShare}>
    <ProjectCard onEdit={handleEdit} onDelete={handleDelete} onShare={handleShare} />
  </ProjectList>
</Dashboard>

// ✅ Compose at the top, each child owns its own concerns
<Dashboard>
  <ProjectList>
    {projects.map(p => (
      <ProjectCard key={p.id} project={p}>
        <ProjectActions projectId={p.id} />
      </ProjectCard>
    ))}
  </ProjectList>
</Dashboard>
```

## Extracting Custom Hooks

### When to Extract

- The same `useState` + `useEffect` combo appears in 2+ components.
- A component has logic unrelated to what it renders.
- You want to test logic independently from UI.

### Naming Convention

- `use<Entity><Action>` - e.g., `useProjectFilters`, `useFormValidation`
- Return an object (not an array) when there are > 2 values.

### Example: Form Logic Extraction

```tsx
// ❌ BEFORE: Logic tangled with JSX
function ProjectForm({ project }: { project?: IProject }) {
  const [name, setName] = useState(project?.name ?? '');
  const [url, setUrl] = useState(project?.url ?? '');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => { /* 20 lines */ };
  const handleSubmit = async () => { /* 30 lines */ };

  return <form>{ /* 80 lines of JSX */ }</form>;
}

// ✅ AFTER: Hook encapsulates form logic, component is pure UI
function useProjectForm(project?: IProject) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: project?.name ?? '',
      url: project?.url ?? '',
    },
  });

  const onSubmit = handleSubmit(async (data) => {
    await saveProject(data);
  });

  return { register, errors, isSubmitting, onSubmit };
}

function ProjectForm({ project }: { project?: IProject }) {
  const { register, errors, isSubmitting, onSubmit } = useProjectForm(project);

  return (
    <form onSubmit={onSubmit}>
      <Input {...register('name')} error={errors.name?.message} />
      <Input {...register('url')} error={errors.url?.message} />
      <Button type="submit" loading={isSubmitting}>Save</Button>
    </form>
  );
}
```

### Example: Data Fetching Extraction

```tsx
// ❌ Fetching + error handling + loading inline
function ProjectDashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjects()
      .then(setProjects)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  // ... rendering
}

// ✅ Encapsulated in a hook
function useProjects() {
  const [projects, setProjects] = useState<IProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetchProjects()
      .then(setProjects)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { projects, loading, error };
}
```

## UI State Management with Zustand

### When to Use Zustand vs Local State

| Scenario | Use |
|---|---|
| Single component toggle/input | `useState` |
| Form state | React Hook Form |
| Shared between sibling components | Zustand |
| Persisted across navigations | Zustand |
| Server/async data | Fetch hook or SWR-style |
| Global UI (modals, toasts, sidebar) | Zustand |

### Zustand Store Patterns

#### Focused Slices (SRP for Stores)

```tsx
// ❌ One mega store
const useStore = create((set) => ({
  projects: [],
  filters: {},
  modals: {},
  notifications: [],
  user: null,
  // 40 actions...
}));

// ✅ Separate stores by domain
const useProjectStore = create<IProjectState>((set) => ({
  projects: [],
  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((s) => ({ projects: [...s.projects, project] })),
  removeProject: (id) => set((s) => ({
    projects: s.projects.filter((p) => p.id !== id),
  })),
}));

const useUIStore = create<IUIState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  activeModal: null,
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}));
```

#### Selector Pattern (Prevent Unnecessary Re-renders)

```tsx
// ❌ Subscribes to entire store — re-renders on ANY change
const { projects, filters } = useProjectStore();

// ✅ Subscribe only to what you need
const projects = useProjectStore((s) => s.projects);
const filters = useProjectStore((s) => s.filters);
```

#### Derived State (Computed Values)

```tsx
// ❌ Storing derived state
const useStore = create((set) => ({
  projects: [],
  activeCount: 0, // redundant — derivable from projects
}));

// ✅ Compute in selector
const activeCount = useProjectStore(
  (s) => s.projects.filter((p) => p.status === 'active').length
);
```

## Conditional Rendering Cleanup

```tsx
// ❌ Nested ternaries
return (
  <div>
    {isLoading ? (
      <Spinner />
    ) : error ? (
      <Error message={error} />
    ) : data.length === 0 ? (
      <Empty />
    ) : (
      <List items={data} />
    )}
  </div>
);

// ✅ Early returns
if (isLoading) return <Spinner />;
if (error) return <Error message={error} />;
if (data.length === 0) return <Empty />;

return <List items={data} />;
```

## Extracting Render Sections

```tsx
// ❌ One huge return block
function Dashboard() {
  return (
    <div>
      {/* 30 lines of header */}
      {/* 40 lines of stats */}
      {/* 60 lines of table */}
      {/* 20 lines of footer */}
    </div>
  );
}

// ✅ Extract sections as components (not helper functions)
function Dashboard() {
  return (
    <div>
      <DashboardHeader />
      <DashboardStats />
      <DashboardTable />
      <DashboardFooter />
    </div>
  );
}
```

**Why components over render functions:** Components have their own render cycle, are independently testable, and show up clearly in React DevTools.

## Event Handler Extraction

```tsx
// ❌ Inline complex handlers
<button onClick={() => {
  setLoading(true);
  api.delete(id).then(() => {
    removeProject(id);
    toast.success('Deleted');
  }).catch(handleError).finally(() => setLoading(false));
}}>
  Delete
</button>

// ✅ Named handler (or in a hook if reused)
const handleDelete = async (id: string) => {
  setLoading(true);
  try {
    await api.delete(id);
    removeProject(id);
    toast.success('Deleted');
  } catch (err) {
    handleError(err);
  } finally {
    setLoading(false);
  }
};

<button onClick={() => handleDelete(id)}>Delete</button>
```

## Props Interface Hygiene

```tsx
// ❌ Passing entire objects when only a few fields are needed
interface IProjectCardProps {
  project: IProject; // component only uses name, url, status
}

// ✅ Accept only what's needed (easier to test, clearer contract)
interface IProjectCardProps {
  name: string;
  url: string;
  status: ProjectStatus;
  onEdit: () => void;
}

// Exception: when the component genuinely operates on the whole entity
// (e.g., a form that edits all fields), passing the full object is fine.
```

## Refactoring Checklist

When refactoring a React component, walk through:

1. **Does this component have a single responsibility?** If not, split it.
2. **Is there duplicated JSX or logic?** Extract shared pieces.
3. **Are there > 3 useState calls?** Consider a custom hook or Zustand.
4. **Is there prop drilling?** Use composition, Zustand, or context.
5. **Are there nested ternaries?** Use early returns or a status map.
6. **Can the logic be tested independently?** Extract into a hook.
7. **Is the component > 150 lines?** Decompose into sub-components.
8. **Are event handlers inline and complex?** Extract to named functions.
9. **Does the Zustand store mix unrelated domains?** Split into slices.
10. **Are selectors subscribing to the full store?** Use focused selectors.

## File Organization After Refactoring

When a component grows sub-components, co-locate them:

```
client/components/projects/
  ProjectDashboard.tsx          # orchestrator
  ProjectStats.tsx              # presentational
  ProjectFilterBar.tsx          # presentational + local state
  ProjectList.tsx               # presentational
  ProjectCard.tsx               # presentational

client/hooks/
  useProjects.ts                # data fetching
  useProjectFilters.ts          # filter logic
  useProjectForm.ts             # form logic
```

Hooks go in `client/hooks/`. Sub-components stay alongside their parent in the same directory.

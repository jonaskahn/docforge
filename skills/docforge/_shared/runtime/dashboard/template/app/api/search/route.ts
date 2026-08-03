import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// static export: pre-render the search index into a plain JSON file at build
// time instead of serving a dynamic API route
export const revalidate = false;
export const { staticGET: GET } = createFromSource(source);

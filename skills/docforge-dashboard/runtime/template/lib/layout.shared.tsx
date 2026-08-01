import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, docsRoute, gitUrl } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: appName,
      url: docsRoute,
    },
    ...(gitUrl ? { githubUrl: gitUrl } : {}),
  };
}

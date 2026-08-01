import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, gitUrl } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: appName,
    },
    ...(gitUrl ? { githubUrl: gitUrl } : {}),
  };
}

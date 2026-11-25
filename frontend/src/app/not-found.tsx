import BaseErrorFallback from '@/components/shared/BaseErrorFallback';

export default function NotFoundPage() {
  return (
    <BaseErrorFallback
      title="Page not found"
      message="The page you are looking for does not exist."
    />
  );
}

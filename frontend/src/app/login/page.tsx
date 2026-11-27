import { Suspense } from 'react';
import AuthFrame from '@/components/auth/AuthFrame';
import LoginForm from '@/components/auth/LoginForm';

export default function LoginPage() {
  return (
    <AuthFrame>
      <Suspense>
        <LoginForm />
      </Suspense>
    </AuthFrame>
  );
}

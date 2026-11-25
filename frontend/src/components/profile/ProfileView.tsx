"use client";

import ChangePasswordForm from "@/components/profile/ChangePasswordForm";
import DisplayNameForm from "@/components/profile/DisplayNameForm";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useProfile from "@/hooks/useProfile";

export default function ProfileView() {
  const {
    user,
    isLoading,
    loadError,
    displayNameError,
    passwordErrors,
    isSavingName,
    isChangingPassword,
    saveDisplayName,
    changePassword,
  } = useProfile();

  if (isLoading) return <BaseLoadingState />;
  if (!user) {
    return (
      <BaseErrorState
        message={loadError ?? "Could not load your profile."}
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-xl flex-col gap-6 p-4">
      <h1 className="text-xl font-semibold text-gray-900">Profile</h1>
      <section className="flex flex-col gap-1 rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-sm font-medium text-gray-900">Email</h2>
        <p className="text-sm text-gray-700">{user.email}</p>
      </section>
      <DisplayNameForm
        initialDisplayName={user.displayName}
        error={displayNameError}
        isSaving={isSavingName}
        onDisplayNameSave={saveDisplayName}
      />
      <ChangePasswordForm
        errors={passwordErrors}
        isSaving={isChangingPassword}
        onPasswordChange={changePassword}
      />
    </main>
  );
}

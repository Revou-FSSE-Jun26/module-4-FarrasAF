import { Suspense } from "react";
import GuestBoardView from "@/components/board/GuestBoardView";
import BaseLoadingState from "@/components/shared/BaseLoadingState";

interface InvitePageParams {
  params: Promise<{ token: string }>;
}

// Reading `params` is runtime data, so it happens inside a Suspense boundary.
async function InviteContent({ params }: InvitePageParams) {
  const { token } = await params;
  return <GuestBoardView token={token} />;
}

export default function InvitePage({ params }: InvitePageParams) {
  return (
    <main className="flex flex-1 flex-col bg-gray-50">
      <Suspense fallback={<BaseLoadingState />}>
        <InviteContent params={params} />
      </Suspense>
    </main>
  );
}

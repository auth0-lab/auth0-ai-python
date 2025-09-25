import { TokenVaultInterrupt } from "@auth0/ai/interrupts";
import type { Interrupt } from "@langchain/langgraph-sdk";

import { EnsureAPIAccess } from "@/components/auth0-ai/TokenVault";

interface TokenVaultInterruptHandlerProps {
  interrupt: Interrupt | undefined | null;
  onFinish: () => void;
  auth?: {
    authorizePath?: string;
    returnTo?: string;
  };
}

export function TokenVaultInterruptHandler({
  interrupt,
  onFinish,
  auth,
}: TokenVaultInterruptHandlerProps) {
  console.log("TokenVaultInterruptHandler - interrupt:", interrupt);
  console.log(
    "TokenVaultInterruptHandler - interrupt.value:",
    interrupt?.value
  );

  if (!interrupt) {
    console.log("TokenVaultInterruptHandler - No interrupt");
    return null;
  }

  const isTokenVaultInterrupt = TokenVaultInterrupt.isInterrupt(
    interrupt.value
  );
  console.log(
    "TokenVaultInterruptHandler - isTokenVaultInterrupt:",
    isTokenVaultInterrupt
  );

  if (!isTokenVaultInterrupt) {
    console.log("TokenVaultInterruptHandler - Not a TokenVault interrupt");
    return null;
  }

  return (
    <div key={interrupt.ns?.join("")} className="whitespace-pre-wrap">
      <EnsureAPIAccess
        mode="popup"
        interrupt={interrupt.value}
        onFinish={onFinish}
        auth={auth}
        connectWidget={{
          title: "Authorization Required.",
          description: interrupt.value.message,
          action: { label: "Authorize" },
        }}
      />
    </div>
  );
}

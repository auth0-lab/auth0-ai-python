import { BrowserView, MobileView } from "react-device-detect";

import type { TokenVaultAuthProps } from "./TokenVaultAuthProps";
import { EnsureAPIAccessPopup } from "./popup";
import { EnsureAPIAccessRedirect } from "./redirect";

export function EnsureAPIAccess(props: TokenVaultAuthProps) {
  const { mode } = props;

  switch (mode) {
    case "popup":
      return <EnsureAPIAccessPopup {...props} />;
    case "redirect":
      return <EnsureAPIAccessRedirect {...props} />;
    case "auto":
    default:
      return (
        <>
          <BrowserView>
            <EnsureAPIAccessPopup {...props} />
          </BrowserView>
          <MobileView>
            <EnsureAPIAccessRedirect {...props} />
          </MobileView>
        </>
      );
  }
}

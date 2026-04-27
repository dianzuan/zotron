// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill
import { onStartup, onShutdown, onMainWindowLoad, onMainWindowUnload } from "./hooks";

// Register on Zotero global (always available in Zotero sandbox)
(Zotero as any).Zotron = {
  hooks: { onStartup, onShutdown, onMainWindowLoad, onMainWindowUnload },
  data: { initialized: false },
};

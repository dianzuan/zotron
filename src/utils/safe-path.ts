// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 diamondrill

/**
 * Safely convert a path string to an nsIFile, handling non-ASCII characters
 * (Chinese, dashes, quotes, etc.) that Zotero.File.pathToFile() sometimes
 * chokes on in certain XPCOM builds.
 */
export function safePathToFile(rawPath: string): any {
  try {
    return Zotero.File.pathToFile(rawPath);
  } catch {
    try {
      const nsFile = (Components.classes as any)["@mozilla.org/file/local;1"]
        .createInstance((Components.interfaces as any).nsIFile);
      nsFile.initWithPath(rawPath);
      return nsFile;
    } catch {
      return null;
    }
  }
}

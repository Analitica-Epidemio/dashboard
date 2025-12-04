/**
 * Block Config Panel - Re-export
 *
 * This file re-exports from the new modular structure.
 * @see ./block-config-panel/index.tsx for the main component
 */

export { BlockConfigPanel } from "./block-config-panel/index";
export { getBlockMeta, isLoopBlock, isMainBlock } from "./block-config-panel/block-metadata";
export type { BlockConfigFormState, BlockConfigData } from "./block-config-panel/types";

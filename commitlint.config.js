module.exports = {
  rules: {
    // Enforce scope pattern: lowercase words OR PascalCase component names (with optional {})
    'scope-pattern': [2, 'always'],
    // Reject WIP and similar draft indicators
    'no-wip': [2, 'always'],
    // Header must not exceed 100 characters
    'header-max-length': [2, 'always', 100],
    // Subject must not be empty
    'subject-empty': [2, 'never'],
    // Subject must not end with period
    'subject-full-stop': [2, 'never', '.'],
  },
  plugins: [
    {
      rules: {
        'scope-pattern': ({ header }) => {
          // Pattern: "scope: description" where scope is either:
          // - lowercase word (cmake, ci, docs, etc.)
          // - PascalCase component name (FindShaderc, VkEncoderConfig, etc.)
          // - Component with braces (VkEncoderConfig{H264,H265})
          const pattern = /^([a-z]+|[A-Z][a-zA-Z0-9]*(\{[^}]+\})?): .+/;
          const valid = pattern.test(header);
          return [
            valid,
            `Commit message must match pattern "scope: description"\n` +
            `  - scope: lowercase (cmake, ci, docs) OR PascalCase (FindShaderc, VkEncoderConfig)\n` +
            `  - Example: "cmake: fix build issue" or "VkEncoderConfig: add new option"\n` +
            `  - Got: "${header}"`,
          ];
        },
        'no-wip': ({ header }) => {
          // Reject commits with draft indicators (case-insensitive)
          const forbidden = /\b(wip|WIP|fixup|FIXUP|squash|SQUASH|tmp|TMP|todo|TODO|hack|HACK|xxx|XXX|do not merge|DO NOT MERGE|dnm|DNM|draft|DRAFT)\b/i;
          const match = header.match(forbidden);
          return [
            !match,
            `Commit message must not contain draft indicators like "${match ? match[0] : 'WIP'}"\n` +
            `  - Forbidden (any case): WIP, fixup, squash, tmp, todo, hack, xxx, do not merge, dnm, draft\n` +
            `  - Got: "${header}"`,
          ];
        },
      },
    },
  ],
};

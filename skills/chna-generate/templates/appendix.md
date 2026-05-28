# Appendix: Data Sources

This report draws exclusively from the documents and platform exports
provided by {{ organization.name }} for the {{ organization.fiscal_year }}
assessment cycle. No external or web-based data was used. Every
statistic and quote in the body of this report is cited inline as
`[source_file:chunk_id]` and indexed below.

## Source documents

{{ For each file in sources.json.files: }}
- **{{ source_file }}** — {{ chunk_count }} extracted chunks

## Citation index

{{ For each cited chunk, ordered by source_file then chunk_id: }}

- `{{ source_file }}:{{ chunk_id }}` — {{ heading_path joined with " > " }}
  > {{ first 240 chars of chunk text, single line }}

## Data limitations

{{ List each section that fell back to "N/A — Limited specific data
available" and the reason. Recommend specific data collection items for
the next assessment cycle. }}

## Methodology

{{ When the user marked a Methodology section for verbatim copy in the
config, this appendix references it rather than duplicating. Otherwise,
the skill leaves this section as a placeholder for the user to author. }}

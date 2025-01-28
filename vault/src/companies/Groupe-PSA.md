```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Groupe-PSA" or company = "Groupe PSA")
sort location, dt_announce desc
```

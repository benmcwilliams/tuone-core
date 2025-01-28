```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Epeu-Next-Level-GmbH" or company = "Epeu Next Level GmbH")
sort location, dt_announce desc
```

```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sinn-Power-GmbH" or company = "Sinn Power GmbH")
sort location, dt_announce desc
```

```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enex-Power-Germany-GmbH" or company = "Enex Power Germany GmbH")
sort location, dt_announce desc
```

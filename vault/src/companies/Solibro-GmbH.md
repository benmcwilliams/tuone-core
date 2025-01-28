```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solibro-GmbH" or company = "Solibro GmbH")
sort location, dt_announce desc
```

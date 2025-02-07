```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Limagrain-Nederland-BV" or company = "Limagrain Nederland BV")
sort location, dt_announce desc
```

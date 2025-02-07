```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Macquarie's-GIG" or company = "Macquarie's GIG")
sort location, dt_announce desc
```

```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Elemental-Strategic-Metals" or company = "Elemental Strategic Metals")
sort location, dt_announce desc
```

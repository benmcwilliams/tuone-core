```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Trisol-82-Srl" or company = "Trisol 82 Srl")
sort location, dt_announce desc
```

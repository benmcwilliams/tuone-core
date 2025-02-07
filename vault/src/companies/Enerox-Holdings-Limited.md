```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enerox-Holdings-Limited" or company = "Enerox Holdings Limited")
sort location, dt_announce desc
```

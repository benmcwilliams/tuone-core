```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Peterson-UK-Limited" or company = "Peterson UK Limited")
sort location, dt_announce desc
```

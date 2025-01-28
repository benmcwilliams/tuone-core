```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "D3IM" or company = "D3IM")
sort location, dt_announce desc
```

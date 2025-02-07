```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "S.N.-Nuclearelectrica-SA" or company = "S.N. Nuclearelectrica SA")
sort location, dt_announce desc
```

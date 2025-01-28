```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PSD-Poland" or company = "PSD Poland")
sort location, dt_announce desc
```

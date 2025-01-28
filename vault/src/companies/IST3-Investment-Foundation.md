```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "IST3-Investment-Foundation" or company = "IST3 Investment Foundation")
sort location, dt_announce desc
```

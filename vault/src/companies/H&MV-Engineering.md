```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "H&MV-Engineering" or company = "H&MV Engineering")
sort location, dt_announce desc
```

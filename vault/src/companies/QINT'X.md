```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "QINT'X" or company = "QINT'X")
sort location, dt_announce desc
```

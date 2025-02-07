```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sosteneo-SGR-SpA" or company = "Sosteneo SGR SpA")
sort location, dt_announce desc
```

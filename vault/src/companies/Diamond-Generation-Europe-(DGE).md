```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Diamond-Generation-Europe-(DGE)" or company = "Diamond Generation Europe (DGE)")
sort location, dt_announce desc
```

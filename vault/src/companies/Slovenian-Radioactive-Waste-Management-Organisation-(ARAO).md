```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Slovenian-Radioactive-Waste-Management-Organisation-(ARAO)" or company = "Slovenian Radioactive Waste Management Organisation (ARAO)")
sort location, dt_announce desc
```

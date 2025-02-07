```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Anglian-Water-Services" or company = "Anglian Water Services")
sort location, dt_announce desc
```

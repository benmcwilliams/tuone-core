```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energie-Beheer-Nederland-(EBN)" or company = "Energie Beheer Nederland (EBN)")
sort location, dt_announce desc
```

import { useState, useMemo } from 'react'
import { Plus, Search, Edit2, Trash2, Building2, Phone } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Dialog } from '@/components/ui/Dialog'
import { useApiGet, useApiDelete } from '@/hooks/useApi'
import type { Customer } from '@/types'
import CustomerForm from '@/components/customer/CustomerForm'

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const { data: customers, isLoading } = useApiGet<Customer[]>('/customers')
  const deleteMutation = useApiDelete<void>('/customers')

  const filteredCustomers = useMemo(() => {
    if (!customers) return []
    if (!searchQuery.trim()) return customers
    const query = searchQuery.trim().toLowerCase()
    return customers.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        (c.contact_person && c.contact_person.toLowerCase().includes(query)) ||
        (c.phone && c.phone.toLowerCase().includes(query))
    )
  }, [customers, searchQuery])

  const handleDelete = () => {
    if (deletingId) {
      deleteMutation.mutate(deletingId)
      setDeletingId(null)
    }
  }

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer)
    setShowForm(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Building2 className="h-8 w-8 text-primary" />
            客户名录
          </h1>
          <p className="text-muted-foreground mt-1">管理客户信息与背景调研结论</p>
        </div>
        <Button onClick={() => { setEditingCustomer(null); setShowForm(true) }} size="lg">
          <Plus className="h-5 w-5" />
          新建客户
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索客户名称、联系人或电话..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground">
          <p>加载中...</p>
        </div>
      ) : filteredCustomers.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <Building2 className="mx-auto h-12 w-12 opacity-50 mb-3" />
          <p className="text-lg">暂无客户</p>
          <p className="text-sm mt-1">点击"新建客户"添加第一个客户</p>
        </div>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>客户名称</TableHead>
                <TableHead>联系人</TableHead>
                <TableHead>电话</TableHead>
                <TableHead>调研结论</TableHead>
                <TableHead>备注</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCustomers.map((customer) => (
                <TableRow key={customer.id}>
                  <TableCell className="font-medium">{customer.name}</TableCell>
                  <TableCell>{customer.contact_person || '-'}</TableCell>
                  <TableCell>
                    {customer.phone ? (
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3 text-muted-foreground" />
                        {customer.phone}
                      </span>
                    ) : (
                      <span className="text-muted-foreground/50">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {customer.notes?.includes('可承接') ? (
                      <Badge variant="secondary">可承接</Badge>
                    ) : customer.notes?.includes('谨慎') ? (
                      <Badge variant="warning">谨慎承接</Badge>
                    ) : customer.notes?.includes('暂不') ? (
                      <Badge variant="destructive">暂不承接</Badge>
                    ) : (
                      <Badge variant="outline">未调研</Badge>
                    )}
                  </TableCell>
                  <TableCell className="max-w-xs truncate">{customer.notes || '-'}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(customer)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setDeletingId(customer.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {showForm && (
        <CustomerForm
          customer={editingCustomer}
          onClose={() => { setShowForm(false); setEditingCustomer(null) }}
        />
      )}

      <Dialog
        open={deletingId !== null}
        onOpenChange={(open) => !open && setDeletingId(null)}
        title="确认删除"
        description="确定要删除该客户吗?此操作不可撤销。"
      >
        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={() => setDeletingId(null)}>
            取消
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending ? '删除中...' : '删除'}
          </Button>
        </div>
      </Dialog>
    </div>
  )
}
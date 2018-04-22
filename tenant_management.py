from __future__ import print_function

import ipaddress
import unicodedata

import creation
import functions
import values
import vmManagement as vmm
from connection import Connection


primary_data, secondary_data, tertiary_data = values.get_value()

#conn = Connection(remote_ip='152.46.18.27', username='ckogant', pkey_path='/root/.ssh/id_rsa')
#functions.get_connection()
#functions.create_gre_tunnel('1.1.1.1', '2.2.2.2', 'gre_test', primary=True)

#primary_conn = Connection(remote_ip='152.46.18.27', username='ckogant', pkey_path='/root/.ssh/id_rsa')
# Example @TODO: Please uncomment them.
# creation.create_tenant(5)


isPrimaryGreCreated=False
isSecondaryGreCreated = False

interface_primary="eth0"
interface_secondary="eth0"
prefix_veth = "Y"

def _check_need_to_create_vxlan_primary(data):
    """
    returns list of cidrs that are common in primary and secondary and tertiary
    """
    ret = []
    flag_s = False
    flag_t = False
    p_cidrs, s_cidrs, t_cidrs = _give_cidr_ps(data)
    #Between Primary and Secondary
    common_cidrs_ps = set(p_cidrs).intersection(set(s_cidrs))
    ret.append(list(common_cidrs_ps))
    #Between Primary and Tertiary
    common_cidrs_pt = set(p_cidrs).intersection(set(t_cidrs))
    ret.append(list(common_cidrs_pt))

    if len(common_cidrs_ps)>0:
        flag_s = True
    if len(common_cidrs_pt)>0:
        flag_t=True
    return flag_s, flag_t

def _check_need_to_create_vxlan_secondary(data):
    """
    returns list of cidrs that are common in primary and secondary and tertiary
    """
    ret = []
    flag_p = False
    flag_t = False
    p_cidrs, s_cidrs, t_cidrs = _give_cidr_ps(data)
    #Between Primary and Secondary
    common_cidrs_ps = set(p_cidrs).intersection(set(s_cidrs))
    ret.append(list(common_cidrs_ps))
    #Between Secondary and Tertiary
    common_cidrs_st = set(s_cidrs).intersection(set(t_cidrs))
    ret.append(list(common_cidrs_st))

    if len(common_cidrs_ps) > 0:
        flag_p = T
    if len(common_cidrs_st) > 0:
        flag_t = True
    return flag_p, flag_t


def _check_need_to_create_vxlan_tertiary(data):
    """
    returns list of cidrs that are common in primary and secondary and tertiary
    """
    ret = []
    flag_s = False
    flag_t = False
    p_cidrs, s_cidrs, t_cidrs = _give_cidr_ps(data)
    #Between Primary and Secondary
    common_cidrs_ts = set(t_cidrs).intersection(set(s_cidrs))
    ret.append(list(common_cidrs_ts))
    #Between Primary and Tertiary
    common_cidrs_pt = set(p_cidrs).intersection(set(t_cidrs))
    ret.append(list(common_cidrs_pt))

    if len(common_cidrs_ts) > 0:
        flag_s = True
    if len(common_cidrs_pt) > 0:
        flag_p = True
    return flag_p, flag_s


def _check_need_to_create_gre_primary(data):
    """
    returns list of cidrs that are common in primary and secondary and tertiary
    """
    ret = []
    flag_s = False
    flag_t = False
    p_cidrs, s_cidrs, t_cidrs = _give_cidr_ps(data)
    #Between Primary and Secondary
    p_cidrs_copy = list(p_cidrs)
    s_cidrs_copy = list(s_cidrs)

    common_cidrs_ps = set(p_cidrs).intersection(set(s_cidrs))
    for i in list(common_cidrs_ps):
        s_cidrs_copy.remove(i)
    for i in list(common_cidrs_ps):
        p_cidrs_copy.remove(i)
    if len(s_cidrs_copy)!=0 or len(p_cidrs_copy)!=0:
        flag_s = True

    #Between Primary and Tertiary
    p_cidrs_copy = list(p_cidrs)
    t_cidrs_copy = list(t_cidrs)

    common_cidrs_pt = set(p_cidrs).intersection(set(t_cidrs))
    for i in list(common_cidrs_pt):
        t_cidrs_copy.remove(i)
    for i in list(common_cidrs_pt):
        p_cidrs_copy.remove(i)
    if len(p_cidrs_copy) != 0 or len(t_cidrs_copy) != 0:
        flag_t = True

    return flag_s, flag_t, s_cidrs, t_cidrs


def _give_cidr_ps(data):
    primary = data.get("primary")
    secondary = data.get("secondary")
    tertiary = data.get("tertiary")

    primary_subnet = primary.get('subnets')
    p_cidrs = []
    for s in primary_subnet:
        sub = s.get('cidr')
        p_cidrs.append(sub)

    secondary_subnet = secondary.get('subnets')
    s_cidrs = []
    for s in secondary_subnet:
        sub = s.get('cidr')
        s_cidrs.append(sub)
    
    tertiary_subnet = tertiary.get('subnets')
    t_cidrs = []
    for s in tertiary_subnet:
        sub = s.get('cidr')
        t_cidrs.append(sub)

    return p_cidrs, s_cidrs, t_cidrs


def run_primary(data, conn):
    primary = data.get("primary")
    tenant_id = data.get("id")
    secondary = data.get("secondary")
    tertiary = data.get("tertiary")

    # Create Tenant
    # functions.get_connection()
    tenant_name = 'T' + str(tenant_id)
    pgw_name = 'PGW-' + tenant_name

    veth_hyp = prefix_veth+'hyp-t' + str(tenant_id) + '-pgw'
    veth_hyp_ip = '99.1.' + str(tenant_id) + '.1/24'
    veth_ns = prefix_veth+'pgw-hyp-t' + str(tenant_id)
    veth_ns_ip = '99.1.' + str(tenant_id) + '.2/24'
    # create a namespace for tenant PGW-T1
    functions.create_namespace(pgw_name, primary=True)
    # Create veth pair in hypervisor  (pgw-hypt1)(1.1.1.1)(<1.1.tenant-id.1>)
    functions.create_vethpair(veth_hyp, veth_ns, primary=True)

    functions.move_veth_to_namespace(veth_ns, pgw_name, primary=True)
    functions.assign_ip_address_namespace(
        pgw_name, veth_ns, veth_ns_ip, primary=True)
    functions.set_link_up_in_namespace(pgw_name, veth_ns, primary=True)
    functions.assign_ip_address(veth_hyp, veth_hyp_ip, primary=True)
    functions.set_link_up(veth_hyp, primary=True)

    # Creating IGW 
    igw_name = 'IGW-' + tenant_name

    veth_hyp_igw = prefix_veth+'hyp-t' + str(tenant_id) + '-igw'
    veth_hyp_igw_ip = '55.1.' + str(tenant_id) + '.1/24'
    veth_igw_hyp = prefix_veth+'igw-hyp-t' + str(tenant_id)
    veth_igw_hyp_ip = '55.1.' + str(tenant_id) + '.2/24'
    # create a namespace for tenant PGW-T1
    functions.create_namespace(igw_name, primary=True)
    # Create veth pair in hypervisor  (pgw-hypt1)(1.1.1.1)(<1.1.tenant-id.1>)
    functions.create_vethpair(veth_hyp_igw, veth_igw_hyp, primary=True)

    functions.move_veth_to_namespace(veth_igw_hyp, igw_name, primary=True)
    functions.assign_ip_address_namespace(
        igw_name, veth_igw_hyp, veth_igw_hyp_ip, primary=True)
    functions.set_link_up_in_namespace(igw_name, veth_igw_hyp, primary=True)
    functions.assign_ip_address(veth_hyp_igw, veth_hyp_igw_ip, primary=True)
    functions.set_link_up(veth_hyp_igw, primary=True)

    # create veth pair between IGW and PGW

    veth_pgw = prefix_veth+'pgw-t' + str(tenant_id) + '-igw'
    veth_pgw_ip = '56.1.' + str(tenant_id) + '.1/24'
    veth_igw = prefix_veth+'igw-pgw-t' + str(tenant_id)
    veth_igw_ip = '56.1.' + str(tenant_id) + '.2/24'
    
    # Create veth pair in hypervisor  (pgw-hypt1)(1.1.1.1)(<1.1.tenant-id.1>)
    functions.create_vethpair(veth_pgw, veth_igw, primary=True)

    functions.move_veth_to_namespace(veth_igw, igw_name, primary=True)
    functions.assign_ip_address_namespace(
        igw_name, veth_igw, veth_igw_ip, primary=True)
    functions.set_link_up_in_namespace(igw_name, veth_igw, primary=True)

    functions.move_veth_to_namespace(veth_pgw, pgw_name, primary=True)
    functions.assign_ip_address_namespace(
        pgw_name, veth_pgw, veth_pgw_ip, primary=True)
    functions.set_link_up_in_namespace(pgw_name, veth_pgw, primary=True)

    # check if vxlan is reqd
    flag_s, flag_t = _check_need_to_create_vxlan_primary(data)

    if flag_s or flag_t:
        # create bridge inside IGW
        vx_bridge_name = 'vx-igw-'+tenant_name
        functions.create_bridge_namespace(igw_name, vx_bridge_name, primary=True)
        vx_device_name = 'vx-igw-'+tenant_name+'-dev'
        vxlan_id = tenant_id
        functions.create_vxlan_tunnel(igw_name,
            vx_device_name, vxlan_id, vx_bridge_name, veth_igw_hyp, primary=True)
        if flag_s:
            remote_ip = '55.2.1.2'
            functions.add_fdb_entry_in_vxlan_default_namespace(igw_name, remote_ip, vx_device_name)

        if flag_t:
            remote_ip = '55.3.1.2'
            functions.add_fdb_entry_in_vxlan_default_namespace(
                igw_name, remote_ip, vx_device_name)
    
    # creating GRE 
    flag_s, flag_t, s_cidrs, t_cidrs = _check_need_to_create_gre_primary(data)

    if flag_s:
        local_ip = veth_igw_hyp_ip
        remote_ip = '55.2.1.2'
        gre_tunnel_name = 'gre-igw-'+tenant_name+'-'+remote_ip
        functions.create_gre_tunnel_namespace(igw_name, remote_ip, local_ip, gre_tunnel_name)
        for subnet in s_cidrs:
            functions.add_route_for_gre_cidr_namespace(igw_name, subnet, gre_tunnel_name)
        





        


    
    
    

    veth_br_t = prefix_veth+tenant_name+'-t'
    veth_t_br = prefix_veth+tenant_name+'t-'
    ip_u = unicode(ip, 'utf-8')
    veth_t_br_ip = str(ipaddress.ip_address(ip_u) + 1)+'/24'

    #add routes for all the primary subnets in primary hypervisor
    functions.add_route_in_hypervisor_non_default(
        veth_ns_ip, cidr, primary=True)

    functions.add_route_in_namespace_non_default(
        ns_name, veth_t_pgw_ip, cidr, primary=True)

    vmm.defineNetwork(conn.primary_conn, bridge_name)


    





def run(data):
    run_primary(data)
    run_secondary(data)
    run_tertiary(data)


